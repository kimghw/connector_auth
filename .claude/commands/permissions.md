/home/kimghw/Connector_auth/.claude/settings.local.json을 확인 후 permission 이 설정되어 있는지 확인하고 없으면, 아래 내용을 설정파일에 등록할지를 물어보고, 있으면 삭제할 거라고 물어본다.
{
  "permissions": {
    "defaultMode": "allow",
    "deny": [
      "Bash(rm -rf /*)",
      "Bash(rm -rf /)",
      "Bash(rm -rf ~)",
      "Bash(rm -rf .)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)",
      "Bash(sudo rm -rf:*)",
      "Bash(chmod 777:*)",
      "Bash(:(){ :|:& };:)"
    ]
  }
}
