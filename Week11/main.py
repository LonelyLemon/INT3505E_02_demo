from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Server running at http://127.0.0.1:5000")
    print("Metrics Prometheus at http://127.0.0.1:5000/metrics")
    app.run(debug=True)