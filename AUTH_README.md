# CapGenie Authentication System

Your CapGenie application now has secure authentication enabled! This means only authorized users can access the application.

## 🔐 Default Login Credentials

The following users are pre-configured:

| Username | Password | Description |
|----------|----------|-------------|
| `admin` | `capgenie2024` | Administrator account |
| `user1` | `password123` | General user account |
| `researcher` | `science2024` | Research account |

## 🚀 How to Access

1. **Visit your application**: https://capgenie-web2-env.eba-hc96g7am.us-east-1.elasticbeanstalk.com
2. **You'll be redirected to the login page**
3. **Enter your credentials** using one of the accounts above
4. **Click "Sign In"** to access the application

## 👥 Managing Users

### Using the Management Script

Run the user management script to add, remove, or modify users:

```bash
python manage_users.py
```

This will give you a menu with options:
- **List users** - See all current users
- **Add new user** - Create a new user account
- **Change password** - Update an existing user's password
- **Exit** - Close the script

### Example: Adding a New User

```bash
$ python manage_users.py

==================================================
CapGenie User Management
==================================================
1. List users
2. Add new user
3. Change password
4. Exit
--------------------------------------------------
Enter your choice (1-4): 2

=== Add New User ===
Enter username: john_doe
Enter password: 
Confirm password: 
Success: User 'john_doe' added successfully!
```

## 🔧 Security Features

- **Password Hashing**: All passwords are securely hashed using Werkzeug
- **Session Management**: Uses Flask-Login for secure session handling
- **Protected Routes**: All application routes require authentication
- **Automatic Logout**: Sessions expire when browser is closed

## 🛡️ Security Best Practices

1. **Change Default Passwords**: Update the default passwords immediately
2. **Use Strong Passwords**: Minimum 6 characters, but recommend 8+ with mixed characters
3. **Regular Updates**: Change passwords periodically
4. **Limited Access**: Only give access to trusted users

## 🔄 Updating Users in Production

After making changes to users locally, you need to redeploy:

```bash
eb deploy
```

## 🚨 Important Notes

- **User data is stored in memory** - this means users will be reset if the server restarts
- **For production use**, consider implementing a database for persistent user storage
- **The current system is suitable for small teams** with trusted users

## 🆘 Troubleshooting

### Can't Login?
1. Check that you're using the correct username/password
2. Ensure the application has been deployed with the latest changes
3. Try clearing your browser cache

### Need to Reset All Users?
Edit the `auth.py` file and redeploy:
```bash
eb deploy
```

### Want to Disable Authentication?
Comment out the `@login_required` decorators in `app.py` and redeploy.

## 📞 Support

If you need help with the authentication system, check the logs:
```bash
eb logs
``` 