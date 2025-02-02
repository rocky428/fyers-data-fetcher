from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import logging
import logging.config

# Configure logging
logging.config.fileConfig("log.conf")
server_logger = logging.getLogger("local_server")

class AuthHandler(BaseHTTPRequestHandler):
    """Handles HTTP GET requests for authentication and extracts an authorization code."""
    
    def do_GET(self):
        """Handles GET requests by extracting the authorization code from the URL parameters.
        If an authorization code is found, it is stored and a confirmation page is sent to the client.
        """
        global auth_code, httpd
        
        # Parse the URL to extract query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "auth_code" in params:
            auth_code = params["auth_code"][0]  # Store the authorization code
            server_logger.info("Authorization Code Received")
            
            # Send a response to the user
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html_content = """
            <html>
                <body>
                    <h1>Authorization Successful</h1>
                    <p>You can close this window.</p>
                </body>
            </html>
            """
            self.wfile.write(html_content.encode("utf-8"))  # Encode as UTF-8
            
            # Stop the server after receiving the auth code
            self.server.auth_code = auth_code
            self.server.running = False  # Set flag to stop the server

    def log_message(self, format, *args):  
        """Overrides default logging to suppress terminal logging."""
        return None 

def run_local_server(port: int):
    """Starts a local HTTP server to receive an authorization code via a GET request.
    
    Args:
        port (int): The port on which the server will listen.
    
    Returns:
        str: The received authorization code.
    """
    server_address = ("", port)
    with HTTPServer(server_address, AuthHandler) as httpd:
        httpd.running = True
        httpd.auth_code = None
        while httpd.running:
            httpd.handle_request()  # This blocks execution until shutdown is called
        auth_code = httpd.auth_code
    return auth_code