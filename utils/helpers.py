def format_nick(original_name: str, role: str) -> str:
    return f"{original_name.split('||')[0].strip()} || {role}"
