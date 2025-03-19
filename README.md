# NYCTransitHub

NYCTransitHub is a web application developed during the LeetCode Bootcamp that provides real-time updates, schedules, and transit information for New York City's public transportation system. By leveraging the MTA API, the app delivers accurate and timely data to enhance the commuting experience.

## Features

- **Real-Time Updates**: Stay informed with live data on train and bus arrivals, service changes, and delays.
- **Schedules**: Access up-to-date schedules for all NYC subway lines and bus routes.
- **Station Information**: Retrieve details about station amenities, accessibility features, and nearby points of interest.

## Installation

To set up the NYCTransitHub application locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AM-git-hub/NYCTransitHub.git
   cd NYCTransitHub
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Obtain an MTA API key by registering at the [MTA Developer Portal](https://api.mta.info/).
   - Create a `.env` file in the project root directory and add your API key:
     ```
     MTA_API_KEY=your_api_key_here
     ```

5. **Initialize the database**:
   ```bash
   flask db upgrade
   ```

6. **Run the application**:
   ```bash
   flask run
   ```
   The application will be accessible at `http://127.0.0.1:5000/`.

## Usage

- **Homepage**: View an overview of current transit conditions, including major service alerts and delays.
- **Search**: Enter a specific station or route to get detailed information and real-time updates.
- **Favorites**: Save frequently accessed stations or routes for quick reference.

## Contributing

We welcome contributions to enhance NYCTransitHub. To contribute:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/your_feature_name
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add a descriptive commit message'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your_feature_name
   ```
5. Open a Pull Request detailing your changes.


## Acknowledgments

- [Metropolitan Transportation Authority (MTA)](https://new.mta.info/) for providing the transit data API.
