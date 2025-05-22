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

def find_cs_files(root_dir: str):
    cs_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude any directory named "Tests" (case-insensitive)
        dirnames[:] = [d for d in dirnames if d.lower() != "tests"]

        for file in filenames:
            if file.lower().endswith(".cs") and "tests" not in file.lower():
                full_path = os.path.join(dirpath, file)
                cs_files.append(full_path)

    return cs_files
