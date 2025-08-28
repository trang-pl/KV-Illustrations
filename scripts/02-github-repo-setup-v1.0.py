#!/usr/bin/env python3
"""
GitHub Repository Setup Script v1.0
Tạo và setup GitHub repository với directories cần thiết
"""

import os
import sys
import requests
from dotenv import load_dotenv
from pathlib import Path

def load_environment():
    """Load environment variables từ .env file"""
    load_dotenv()
    
    github_pat = os.getenv('GITHUB_PAT')
    git_repo_path = os.getenv('GIT_REPO_PATH')
    github_owner = os.getenv('GITHUB_REPO_OWNER')
    github_repo_name = os.getenv('GITHUB_REPO_NAME')
    
    if not all([github_pat, git_repo_path, github_owner, github_repo_name]):
        raise ValueError("Thiếu environment variables: GITHUB_PAT, GIT_REPO_PATH, GITHUB_REPO_OWNER, GITHUB_REPO_NAME")
    
    return github_pat, git_repo_path, github_owner, github_repo_name

def check_repo_exists(owner, repo_name, token):
    """Kiểm tra repository có tồn tại không qua GitHub API"""
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Lỗi khi kiểm tra repo: {e}")
        return False

def create_repo(owner, repo_name, token):
    """Tạo repository mới với full permissions"""
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": repo_name,
        "private": False,
        "auto_init": True,
        "description": "Repository được tạo tự động bởi script setup"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Đã tạo repository: {owner}/{repo_name}")
        return True
    except requests.HTTPError as e:
        print(f"Lỗi khi tạo repo: {e}")
        if response.status_code == 422:
            print("Repository đã tồn tại hoặc tên không hợp lệ")
        return False
    except requests.RequestException as e:
        print(f"Lỗi network khi tạo repo: {e}")
        return False

def setup_directories(repo_path):
    """Setup directories cần thiết trong local repository"""
    directories = ['assets', 'exports', 'docs']
    
    try:
        repo_dir = Path(repo_path)
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        for dir_name in directories:
            dir_path = repo_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"Đã tạo directory: {dir_path}")
        
        return True
    except Exception as e:
        print(f"Lỗi khi tạo directories: {e}")
        return False

def main():
    """Main function để chạy script"""
    try:
        print("Bắt đầu setup GitHub repository...")
        
        # Load environment
        github_pat, git_repo_path, github_owner, github_repo_name = load_environment()
        
        # Kiểm tra repo tồn tại
        if check_repo_exists(github_owner, github_repo_name, github_pat):
            print(f"Repository {github_owner}/{github_repo_name} đã tồn tại")
        else:
            print(f"Repository {github_owner}/{github_repo_name} chưa tồn tại, đang tạo mới...")
            if not create_repo(github_owner, github_repo_name, github_pat):
                sys.exit(1)
        
        # Setup directories
        if setup_directories(git_repo_path):
            print("Hoàn thành setup directories")
        else:
            sys.exit(1)
        
        print("Script hoàn thành thành công!")
        
    except ValueError as e:
        print(f"Lỗi cấu hình: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()