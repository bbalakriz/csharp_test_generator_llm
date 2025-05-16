import os
import shutil
import logging
from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from typing import Generator, Tuple

logger = logging.getLogger(__name__)

def get_repo(local_dir: str, repo_url: str, branch: str = "main") -> Repo:
    """
    just clone or update a Git repository.
    returns a GitPython Repo object.
    """
    try:
        if os.path.isdir(local_dir) and os.listdir(local_dir):
            logger.info(f"Opening existing repo in {local_dir}")
            repo = Repo(local_dir)
            if repo.remotes.origin.url != repo_url:
                logger.warning("Origin URL mismatch; recloning.")
                shutil.rmtree(local_dir)
                repo = Repo.clone_from(repo_url, local_dir, branch=branch)
            else:
                repo.git.fetch(prune=True)
                repo.git.checkout(branch)
                repo.remotes.origin.pull()
        else:
            logger.info(f"Cloning {repo_url} into {local_dir}")
            os.makedirs(local_dir, exist_ok=True)
            repo = Repo.clone_from(repo_url, local_dir, branch=branch)
        logger.info(f"Repo ready at {local_dir} on branch {branch}")
        return repo
    except (GitCommandError, InvalidGitRepositoryError, NoSuchPathError) as e:
        logger.error(f"Git error: {e}")
        raise

def find_cs_files(path: str, exclude_dirs: Tuple[str, ...] = ("bin", "obj", ".git")) -> Generator[str, None, None]:
    """
    yield the all .cs files under `path`, skipping `exclude_dirs`.
    """
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        for f in files:
            if f.endswith(".cs"):
                yield os.path.join(root, f)
