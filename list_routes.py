from new_structure import create_app

app = create_app()

print("Available routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")
