import requests
import getpass
import re

class ProfessorRatingClient:
    def __init__(self):
        self.base_url = None
        self.token = None
    
    def validate_email(self, email):
        # Validate email format using a regular expression
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    def register(self):
        # Handle user registration with input validation
        try:
            if len(input("Username: ").strip()) > 150:
                raise ValueError("Username must be less than 150 characters")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = getpass.getpass("Password: ").strip()

            if not all([username, email, password]):
                raise ValueError("All fields are required")

            if len(username) > 150:
                raise ValueError("Username too long (max 150 characters)")
                
            if len(email) > 254:
                raise ValueError("Email too long (max 254 characters)")
                
            if not self.validate_email(email):
                raise ValueError("Invalid email format")

            response = requests.post(
                f"{self.base_url}/api/register/",
                data={'username': username, 'email': email, 'password': password}
            )

            if response.status_code == 201:
                print("Registration successful!")
            else:
                error_msg = response.json().get('error', 'Unknown error')
                raise ValueError(f"Registration failed: {error_msg}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    def login(self, url):
        # Handle login by validating URL and credentials, then retrieving the auth token
        try:
            if not url:
                raise ValueError("URL is required")

            # Basic URL validation
            if ' ' in url:
                raise ValueError("URL contains invalid spaces")
                
            if url.startswith("http://"):
                self.base_url = url
            else:
                self.base_url = f"http://{url}"

            username = input("Username: ").strip()
            password = getpass.getpass("Password: ").strip()

            if not username or not password:
                raise ValueError("Both username and password are required")

            response = requests.post(
                f"{self.base_url}/api-token-auth/",
                data={'username': username, 'password': password}
            )

            if response.status_code == 200:
                self.token = response.json()['token']
                print("Login successful!")
            else:
                error_msg = response.json().get('non_field_errors', ['Invalid credentials'])[0]
                raise ValueError(f"Login failed: {error_msg}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to server. Check URL and network connection.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    def logout(self):
        # Log out by resetting the auth token
        self.token = None
        print("Logged out successfully.")

    def list_modules(self):
        # Retrieve and display module instances from the API
        try:
            if not self.token:
                raise ValueError("You must be logged in to list modules")

            headers = {'Authorization': f'Token {self.token}'}
            response = requests.get(f"{self.base_url}/api/module-instances/", headers=headers)

            if response.status_code == 200:
                instances = response.json()
                if not instances:
                    print("No module instances found")
                    return

                print("\nModule Instances:")
                for instance in instances:
                    print(f"\nCode: {instance['module']['code']}, Name: {instance['module']['name']}")
                    print(f"Year: {instance['year']}, Semester: {instance['semester']}")
                    print("Taught by:")
                    for prof in instance['professors']:
                        print(f"  {prof['id']}, {prof['name']}")
            else:
                raise ValueError(f"Server error: {response.json().get('detail', 'Unknown error')}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    def view_ratings(self):
        # Retrieve and display professor ratings from the API
        try:
            if not self.token:
                raise ValueError("You must be logged in to view ratings")

            headers = {'Authorization': f'Token {self.token}'}
            response = requests.get(f"{self.base_url}/api/professors/", headers=headers)

            if response.status_code == 200:
                professors = response.json()
                if not professors:
                    print("No professor ratings found")
                    return

                print("\nProfessor Ratings:")
                for prof in professors:
                    stars = '*' * prof['rating']
                    print(f"The rating of {prof['name']} ({prof['id']}) is {stars}")
            else:
                raise ValueError(f"Server error: {response.json().get('detail', 'Unknown error')}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    def average_rating(self, professor_id, module_code):
        # Retrieve and display the average rating for a professor in a specific module
        try:
            if not professor_id or not module_code:
                raise ValueError("Both professor ID and module code are required")

            if len(professor_id) > 10:
                raise ValueError("Professor ID too long (max 10 characters)")
                
            if len(module_code) > 10:
                raise ValueError("Module code too long (max 10 characters)")

            headers = {'Authorization': f'Token {self.token}'}
            response = requests.get(
                f"{self.base_url}/api/professors/{professor_id}/modules/{module_code}/average/",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                stars = '*' * data['average_rating']
                print(f"\nThe rating of {data['professor_name']} ({data['professor_id']}) "
                      f"in module {data['module_name']} ({data['module_code']}) is {stars}")
            else:
                error_msg = response.json().get('error', 'Unknown error')
                raise ValueError(f"Error: {error_msg}")

        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
    
    def rate_professor(self, professor_id, module_code, year, semester, rating):
        # Submit a rating for a professor for a specific module instance
        try:
            if not all([professor_id, module_code, year, semester, rating]):
                raise ValueError("All fields are required")

            if len(professor_id) > 10:
                raise ValueError("Professor ID too long (max 10 characters)")
                
            if len(module_code) > 10:
                raise ValueError("Module code too long (max 10 characters)")
            
            if not int(semester):
                raise ValueError("Semester must be a valid integer")
            
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    raise ValueError("Rating must be between 1-5")
            except ValueError:
                raise ValueError("Rating must be a valid integer")
            
            headers = {'Authorization': f'Token {self.token}'}
            data = {
                'professor': professor_id,
                'module_code': module_code,
                'year': year,
                'semester': semester,
                'rating': rating
            }
            response = requests.post(f"{self.base_url}/api/ratings/", headers=headers, json=data)
            
            if response.status_code == 201:
                print("Rating submitted successfully!")
            else:
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = response.text
                print(f"Error submitting rating: {error_data}")
        except ValueError as ve:
            print(f"Error: {ve}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    client = ProfessorRatingClient()
    print("Professor Rating System Client")
    print("Available commands: register, login, logout, list, view, average, rate, exit")
    
    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            if not command:
                continue
                
            cmd = command[0].lower()
            
            if cmd == "register":
                if len(command) > 1:
                    print("Error: 'register' command doesn't accept arguments")
                    continue
                client.register()
            elif cmd == "login":
                if len(command) < 2:
                    print("Usage: login <url>")
                    continue
                client.login(command[1])
            elif cmd == "logout":
                if len(command) > 1:
                    print("Error: 'logout' command doesn't accept arguments")
                    continue
                client.logout()
            elif cmd == "list":
                if len(command) > 1:
                    print("Error: 'list' command doesn't accept arguments")
                    continue
                client.list_modules()
            elif cmd == "view":
                if len(command) > 1:
                    print("Error: 'view' command doesn't accept arguments")
                    continue
                client.view_ratings()
            elif cmd == "average":
                if len(command) != 3:
                    print("Usage: average <professor_id> <module_code>")
                    continue
                client.average_rating(command[1], command[2])
            elif cmd == "rate":
                if len(command) != 6:
                    print("Usage: rate <professor_id> <module_code> <year> <semester> <rating>")
                    continue
                try:
                    client.rate_professor(command[1], command[2], int(command[3]), 
                                        int(command[4]), int(command[5]))
                except ValueError:
                    print("Invalid numeric input")
            elif cmd == "exit":
                break
            else:
                print("Invalid command. Available commands: register, login, logout, list, view, average, rate, exit")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error processing command: {str(e)}")