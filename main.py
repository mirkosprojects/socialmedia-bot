from website import create_app

app = create_app()

if __name__ == "__main__":
    # url = 'http://127.0.0.1:5001'
    # webbrowser.open_new(url)
    app.run(debug=True, host="0.0.0.0", port=5001)