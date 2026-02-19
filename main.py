import docker
from pathlib import Path
from abc import ABC
from typing import List, Optional
import tempfile
import tarfile


class DockerHoneypot(ABC):
    def __init__(
        self,
        image: str = None,
        dockerfile_path: str = None,
        image_tag: str = None,
        honeypot_save_path: str = None,
        filter_extensions: Optional[List[str]] = None,
        filter_paths: Optional[List[str]] = None,
    ):

        self.client = docker.from_env()

        if honeypot_save_path is None:
            raise ValueError("Please provide a save path for the honeypot")
        else:
            self.honeypot_save_path = Path(honeypot_save_path)

        if image is not None:
            self.image = image
            self.source = self.image
        elif dockerfile_path is not None:
            self.dockerfile_path = dockerfile_path
            self.image_tag = image_tag

            (self.built_image, build_logs) = self.client.images.build(
                path=self.dockerfile_path, tag=self.image_tag
            )
            self.source = self.built_image.id
        else:
            raise ValueError("Please provide either image or dockerfile_path")

        self.filter_extensions = filter_extensions

        self.filter_paths = filter_paths

    def start(self):
        self.container = self.client.containers.run(
            self.source,
            detach=True,
            auto_remove=True,
            cpu_count=1,
            mem_limit="1g",
            cap_drop=["ALL"],
            cap_add=["CHOWN"],
            security_opt=["no-new-privileges"],
            network="bridge",
            ports={"5000": "5000"},
            # read_only=True,
        )
        self.container.reload()

    @staticmethod
    def copy_file(
        container: docker.models.containers.Container,
        source_path: str,
        destination_path: str,
    ) -> None:
        """
        Copy a single file from container to host.
        """

        dest_path = Path(destination_path)
        dest_path.mkdir(parents=True, exist_ok=True)

        try:
            stream, stat = container.get_archive(source_path)
        except docker.errors.NotFound:
            raise FileNotFoundError(f"{source_path} not found in container")

        # Write tar stream to temp file
        with tempfile.NamedTemporaryFile() as tmp:
            for chunk in stream:
                tmp.write(chunk)
            tmp.flush()

            with tarfile.open(tmp.name) as tar:
                members = tar.getmembers()
                if not members:
                    raise RuntimeError("Empty archive returned from container")

                # Extract only the file (strip internal path)
                member = members[0]
                member.name = Path(member.name).name  # Prevent nested dirs
                tar.extract(member, path=dest_path)

                dest_file = dest_path / member.name

        if dest_file.is_file():
            print(f"Successfully wrote file {dest_file.resolve()}")
        else:
            raise RuntimeError("Unable to write file")

    def copy_file_changes(self):
        changed_files = self.container.diff()

        changed_files = [files["Path"] for files in changed_files if files["Kind"] == 1]

        ## don't copy excluded extensions
        if self.filter_extensions is not None:
            changed_files = [
                file
                for file in changed_files
                if file.suffix not in self.filter_extensions
            ]

        ## don't copy excluded excluded paths

        if self.filter_paths is not None:
            changed_files = [
                file
                for file in changed_files
                if any(file.is_relative_to(path) for path in self.filter_paths)
            ]

        [
            self.copy_file(self.container, file, self.honeypot_save_path)
            for file in changed_files
        ]

    def __del__(self):
        try:
            if hasattr(self, "container") is not None:
                self.stop()
        except AttributeError as e:
            ## attribute error means that container has been deleted from the object
            ## and is probably going to be destroyed
            del e
            pass

    def stop(self):
        try:
            self.container.stop()
            self.container.wait(timeout=30)
            self.container.reload()
            del self.container
        except docker.errors.APIError:
            print("Probably container is already being destroyed.")


if __name__ == "__main__":
    honeypot = DockerHoneypot(
        dockerfile_path="./",
        honeypot_save_path="/tmp/docker_honeypot",
        image_tag="mcp_terminal_honeypot",
    )

    print("Starting Honeypot")

    honeypot.start()

    print("Started honeypot")

    import time

    time.sleep(30)

    print("Copying file changes")

    honeypot.copy_file_changes()

    print("Tearing down environment")
    honeypot.stop()
