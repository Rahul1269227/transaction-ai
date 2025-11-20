"""
Setup branch protection rules for the main branch using GitHub API

This script configures branch protection rules for the main branch to ensure:
- Pull request reviews are required before merging
- Status checks must pass
- Branches must be up to date
- Force pushes and deletions are prevented
- Administrators are subject to the same rules

Usage:
    python scripts/setup_branch_protection.py --token <GITHUB_TOKEN> [--repo <owner/repo>] [--branch main]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token (required if not provided via --token)
    GITHUB_REPOSITORY: Repository in format owner/repo (optional, will try to detect from git)
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# Add parent directory to path for imports
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))


def get_repo_from_git() -> Optional[str]:
    """Try to get repository owner/name from git remote"""
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Handle both SSH and HTTPS URLs
        if url.startswith("git@"):
            # SSH: git@github.com:owner/repo.git
            parts = url.replace("git@github.com:", "").replace(".git", "")
        elif url.startswith("https://"):
            # HTTPS: https://github.com/owner/repo.git
            parts = url.replace("https://github.com/", "").replace(".git", "")
        else:
            return None
            
        return parts
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def setup_branch_protection(
    token: str,
    repo: str,
    branch: str = "main",
    require_reviews: bool = True,
    required_approvals: int = 1,
    dismiss_stale_reviews: bool = True,
    require_code_owner_reviews: bool = False,
    require_status_checks: bool = True,
    required_status_checks: Optional[list] = None,
    require_branches_up_to_date: bool = True,
    enforce_admins: bool = True,
    allow_force_pushes: bool = False,
    allow_deletions: bool = False,
    block_creations: bool = False,
    required_conversation_resolution: bool = True,
    require_linear_history: bool = False,
    require_signed_commits: bool = False,
) -> Dict[str, Any]:
    """
    Set up branch protection rules for a GitHub repository branch
    
    Args:
        token: GitHub personal access token with repo admin permissions
        repo: Repository in format owner/repo
        branch: Branch name to protect (default: main)
        require_reviews: Require pull request reviews before merging
        required_approvals: Number of required approvals (default: 1)
        dismiss_stale_reviews: Dismiss stale pull request approvals when new commits are pushed
        require_code_owner_reviews: Require review from code owners
        require_status_checks: Require status checks to pass before merging
        required_status_checks: List of required status check contexts (optional)
        require_branches_up_to_date: Require branches to be up to date before merging
        enforce_admins: Enforce restrictions for administrators
        allow_force_pushes: Allow force pushes (default: False)
        allow_deletions: Allow branch deletion (default: False)
        block_creations: Block creating the branch if it doesn't exist
        required_conversation_resolution: Require conversation resolution before merging
        require_linear_history: Require linear commit history
        require_signed_commits: Require signed commits
        
    Returns:
        Dict with API response
        
    Raises:
        requests.HTTPError: If API request fails
    """
    url = f"https://api.github.com/repos/{repo}/branches/{branch}/protection"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    # Build protection payload
    protection_data: Dict[str, Any] = {
        "required_status_checks": None,
        "enforce_admins": enforce_admins,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": allow_force_pushes,
        "allow_deletions": allow_deletions,
        "block_creations": block_creations,
        "required_conversation_resolution": required_conversation_resolution,
        "lock_branch": False,
        "allow_fork_syncing": False,
    }
    
    # Configure status checks
    if require_status_checks:
        protection_data["required_status_checks"] = {
            "strict": require_branches_up_to_date,
            "contexts": required_status_checks or [],
        }
    
    # Configure pull request reviews
    if require_reviews:
        protection_data["required_pull_request_reviews"] = {
            "required_approving_review_count": required_approvals,
            "dismiss_stale_reviews": dismiss_stale_reviews,
            "require_code_owner_reviews": require_code_owner_reviews,
            "require_last_push_approval": False,
        }
    
    # Restrictions (set to None to allow all users, or specify teams/users)
    # Leaving as None means no restrictions on who can push
    protection_data["restrictions"] = None
    
    # Additional options
    if require_linear_history:
        protection_data["required_linear_history"] = True
    
    if require_signed_commits:
        protection_data["require_signed_commits"] = True
    
    print(f"Setting up branch protection for {repo}/{branch}...")
    print(f"  - Require PR reviews: {require_reviews} ({required_approvals} approvals)")
    print(f"  - Require status checks: {require_status_checks}")
    print(f"  - Require branches up to date: {require_branches_up_to_date}")
    print(f"  - Enforce for admins: {enforce_admins}")
    print(f"  - Allow force pushes: {allow_force_pushes}")
    print(f"  - Allow deletions: {allow_deletions}")
    print(f"  - Require conversation resolution: {required_conversation_resolution}")
    
    response = requests.put(url, headers=headers, json=protection_data)
    
    if response.status_code == 200:
        print(f"✅ Successfully configured branch protection for {branch}")
        return response.json()
    elif response.status_code == 404:
        error_msg = response.json().get("message", "Unknown error")
        raise requests.HTTPError(
            f"Branch or repository not found: {error_msg}. "
            f"Make sure the branch '{branch}' exists and you have admin access."
        )
    elif response.status_code == 403:
        error_msg = response.json().get("message", "Unknown error")
        raise requests.HTTPError(
            f"Permission denied: {error_msg}. "
            f"Make sure your token has 'repo' admin permissions."
        )
    else:
        error_msg = response.json().get("message", "Unknown error")
        raise requests.HTTPError(
            f"Failed to set branch protection: {error_msg} (Status: {response.status_code})"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Set up branch protection rules for GitHub repository"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
        default=os.getenv("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="Repository in format owner/repo (or set GITHUB_REPOSITORY env var)",
        default=os.getenv("GITHUB_REPOSITORY"),
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="main",
        help="Branch to protect (default: main)",
    )
    parser.add_argument(
        "--required-approvals",
        type=int,
        default=1,
        help="Number of required PR approvals (default: 1)",
    )
    parser.add_argument(
        "--require-code-owner",
        action="store_true",
        help="Require review from code owners",
    )
    parser.add_argument(
        "--no-status-checks",
        action="store_true",
        help="Don't require status checks (default: require them)",
    )
    parser.add_argument(
        "--required-status-checks",
        type=str,
        nargs="+",
        help="List of required status check contexts",
    )
    parser.add_argument(
        "--allow-force-push",
        action="store_true",
        help="Allow force pushes (default: False)",
    )
    parser.add_argument(
        "--allow-deletions",
        action="store_true",
        help="Allow branch deletions (default: False)",
    )
    parser.add_argument(
        "--no-enforce-admins",
        action="store_true",
        help="Don't enforce restrictions for administrators",
    )
    
    args = parser.parse_args()
    
    # Validate token
    if not args.token:
        print("❌ Error: GitHub token is required")
        print("   Provide via --token argument or GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    # Get repository
    repo = args.repo
    if not repo:
        repo = get_repo_from_git()
        if not repo:
            print("❌ Error: Repository not specified and couldn't detect from git")
            print("   Provide via --repo argument or GITHUB_REPOSITORY environment variable")
            sys.exit(1)
    
    print(f"Repository: {repo}")
    print(f"Branch: {args.branch}")
    print()
    
    try:
        result = setup_branch_protection(
            token=args.token,
            repo=repo,
            branch=args.branch,
            required_approvals=args.required_approvals,
            require_code_owner_reviews=args.require_code_owner,
            require_status_checks=not args.no_status_checks,
            required_status_checks=args.required_status_checks,
            allow_force_pushes=args.allow_force_push,
            allow_deletions=args.allow_deletions,
            enforce_admins=not args.no_enforce_admins,
        )
        print()
        print("✅ Branch protection configured successfully!")
        return 0
    except requests.HTTPError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
