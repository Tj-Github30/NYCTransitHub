// Import Socket.IO library if you haven't already
// <script src="/socket.io/socket.io.js"></script>

// Get the custom domain from Flask app's configuration
var customDomain = "{{ app.config['CROSS_ORIGIN'] }}";

// Establish WebSocket connection with custom domain
var socket = io.connect('http://' + customDomain + ':' + location.port);


// Event handler for successful connection
socket.on('connect', function() {
    console.log('Connected to server');
});

// Event handler for disconnection
socket.on('disconnect', function() {
    console.log('Disconnected from server');
});

// Example: Send a message to the server
function sendMessage() {
    var message = 'Hello, Server!';
    socket.emit('message', message); // Send message to server
}

// Example: Receive a message from the server
socket.on('message', function(message) {
    console.log('Received message from server:', message);
    // Handle the received message as needed
});
