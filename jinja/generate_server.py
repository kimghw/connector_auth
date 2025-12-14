"""
Generate server.py from Jinja2 template using tool definitions
"""
import os
import sys
from jinja2 import Template
from pathlib import Path

# Add parent directory to path for importing tool_definitions
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, os.path.join(parent_dir, 'outlook_mcp', 'mcp_server'))

from tool_definitions import MCP_TOOLS


# Handler implementations mapping
HANDLER_IMPLEMENTATIONS = {
    "query_emails": {
        "handler_name": "query_emails",
        "handler_description": "Route to GraphMailQuery.query_filter",
        "custom_logic": """user_email = args["user_email"]
filter_dict = args.get("filter", {})
exclude_dict = args.get("exclude", {})
select_dict = args.get("select", {})

# Convert dicts to parameter objects
filter_params = FilterParams(**filter_dict) if filter_dict else FilterParams()
exclude_params = ExcludeParams(**exclude_dict) if exclude_dict else None
select_params = SelectParams(**select_dict) if select_dict else None

return await graph_mail_query.query_filter(
    user_email=user_email,
    filter=filter_params,
    exclude=exclude_params,
    select=select_params,
    top=args.get("top", 10),
    orderby=args.get("orderby", "receivedDateTime desc")
)"""
    },
    "get_email": {
        "handler_name": "get_email",
        "handler_description": "Route to GraphMailClient.get_message",
        "custom_logic": """return await graph_mail_client.get_message(
    user_email=args["user_email"],
    message_id=args["message_id"]
)"""
    },
    "get_email_attachments": {
        "handler_name": "get_attachments",
        "handler_description": "Route to GraphMailClient.get_attachments",
        "custom_logic": """return await graph_mail_client.get_attachments(
    user_email=args["user_email"],
    message_id=args["message_id"]
)"""
    },
    "download_attachment": {
        "handler_name": "download_attachment",
        "handler_description": "Route to GraphMailClient.download_attachment",
        "custom_logic": """return await graph_mail_client.download_attachment(
    user_email=args["user_email"],
    message_id=args["message_id"],
    attachment_id=args["attachment_id"],
    save_path=args.get("save_path")
)"""
    },
    "search_emails_by_date": {
        "handler_name": "search_by_date",
        "handler_description": "Route to search by date using query_filter",
        "custom_logic": """filter_params = FilterParams(
    received_after=args["start_date"],
    received_before=args["end_date"]
)

select_params = None
if args.get("select_fields"):
    fields = [f.strip() for f in args["select_fields"].split(",")]
    select_params = SelectParams(fields=fields)

return await graph_mail_query.query_filter(
    user_email=args["user_email"],
    filter=filter_params,
    select=select_params,
    top=args.get("top", 10),
    orderby=args.get("orderby", "receivedDateTime desc")
)"""
    },
    "send_email": {
        "handler_name": "send_email",
        "handler_description": "Route to GraphMailClient.send_mail",
        "custom_logic": """return await graph_mail_client.send_mail(
    user_email=args["user_email"],
    to_recipients=args["to_recipients"],
    subject=args["subject"],
    body=args["body"],
    cc_recipients=args.get("cc_recipients", []),
    bcc_recipients=args.get("bcc_recipients", []),
    importance=args.get("importance", "normal"),
    body_type=args.get("body_type", "text"),
    attachments=args.get("attachments", [])
)"""
    },
    "reply_to_email": {
        "handler_name": "reply_email",
        "handler_description": "Route to GraphMailClient.reply_to_message",
        "custom_logic": """if args.get("reply_all", False):
    return await graph_mail_client.reply_all(
        user_email=args["user_email"],
        message_id=args["message_id"],
        comment=args["comment"]
    )
else:
    return await graph_mail_client.reply_to_message(
        user_email=args["user_email"],
        message_id=args["message_id"],
        comment=args["comment"]
    )"""
    },
    "forward_email": {
        "handler_name": "forward_email",
        "handler_description": "Route to GraphMailClient.forward_message",
        "custom_logic": """return await graph_mail_client.forward_message(
    user_email=args["user_email"],
    message_id=args["message_id"],
    to_recipients=args["to_recipients"],
    comment=args.get("comment", "")
)"""
    },
    "delete_email": {
        "handler_name": "delete_email",
        "handler_description": "Route to GraphMailClient.delete_message",
        "custom_logic": """return await graph_mail_client.delete_message(
    user_email=args["user_email"],
    message_id=args["message_id"]
)"""
    },
    "mark_as_read": {
        "handler_name": "mark_read",
        "handler_description": "Route to GraphMailClient.mark_as_read",
        "custom_logic": """return await graph_mail_client.mark_as_read(
    user_email=args["user_email"],
    message_id=args["message_id"],
    is_read=args.get("is_read", True)
)"""
    }
}


def generate_server(output_path: str = None):
    """Generate server.py from template"""

    # Load template
    template_path = Path(__file__).parent / "server_template.j2"
    with open(template_path, 'r') as f:
        template = Template(f.read())

    # Prepare tools data with handler information
    tools_data = []
    for tool in MCP_TOOLS:
        tool_name = tool["name"]
        tool_info = {
            "name": tool_name,
            "handler_name": HANDLER_IMPLEMENTATIONS.get(tool_name, {}).get("handler_name", tool_name),
            "handler_description": HANDLER_IMPLEMENTATIONS.get(tool_name, {}).get(
                "handler_description",
                f"Handler for {tool_name}"
            ),
            "custom_logic": HANDLER_IMPLEMENTATIONS.get(tool_name, {}).get("custom_logic", None)
        }
        tools_data.append(tool_info)

    # Render template
    rendered = template.render(
        server_title="Outlook MCP Server",
        server_version="1.0.0",
        server_name="outlook-mcp-server",
        protocol_version="0.1.0",
        host="0.0.0.0",
        port=3000,
        tools=tools_data
    )

    # Write output
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = Path(__file__).parent / "generated_server.py"

    with open(output_file, 'w') as f:
        f.write(rendered)

    print(f"Server generated successfully at: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    # Generate server.py in the same directory
    output = None
    if len(sys.argv) > 1:
        output = sys.argv[1]

    generate_server(output)