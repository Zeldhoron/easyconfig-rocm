def parse_hook(ec, *args, **kwargs):
    """Example parse hook to replace OpenSSL 3 with system OpenSSL 1.1 for Rust."""
    if ec['name'] == 'cURL':
        # Iterate over the dependencies and replace OpenSSL 3 with system OpenSSL 1.1
        new_deps = []
        for dep in ec['dependencies']:
            if dep[0] == 'OpenSSL' and dep[1] == '3':
                new_deps.append(('OpenSSL', '1.1.1'))  
            else:
                new_deps.append(dep)
        ec['dependencies'] = new_deps

