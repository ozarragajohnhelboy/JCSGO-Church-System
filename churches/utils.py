def detect_church_from_email(email):
    """Detect church based on email domain"""
    email_domain = email.split('@')[1].lower() if '@' in email else ''
    
    # Map email domains to church domains
    email_to_church = {
        'kasiglahan.jcsgo.com': 'kasiglahan',
        'sanjose.jcsgo.com': 'sanjose',
        'christinville.jcsgo.com': 'christinville',
        'tabak.jcsgo.com': 'tabak',
        '10amfamily.jcsgo.com': '10amfamily',
        '3pmfamily.jcsgo.com': '3pmfamily',
    }
    
    return email_to_church.get(email_domain, None)


def generate_church_email(username, church_domain):
    """Generate full email address from username and church domain"""
    return f"{username}@{church_domain}.jcsgo.com" 