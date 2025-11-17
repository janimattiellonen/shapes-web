# Shape Detection Web App

A modern web application for detecting geometric shapes (circles, triangles, rectangles) in images using a trained Keras CNN model. Built with React 19, FastAPI, and TensorFlow.

![Shape Detection Demo](docs/images/demo.png)

## Features

- 🎯 **High Accuracy**: 99%+ shape detection accuracy using deep learning
- 🖼️ **Easy Upload**: Drag-and-drop or click to upload images
- ⚡ **Fast Processing**: Real-time predictions (~50ms per image)
- 📊 **Detailed Results**: Confidence scores and probability distributions
- 🎨 **Modern UI**: Clean, responsive interface with animations
- 🐳 **Dockerized Backend**: Easy deployment with Docker

## Technology Stack

### Frontend
- **React 19** - Latest React with improved performance
- **Vite** - Fast build tool and dev server
- **TypeScript** - Type-safe development

### Backend
- **FastAPI** - Modern Python web framework
- **TensorFlow 2.16** - Deep learning framework
- **Keras** - High-level neural networks API
- **Docker** - Containerization

### ML Model
- **Architecture**: Convolutional Neural Network (CNN)
- **Classes**: Circle, Triangle, Rectangle
- **Input**: 128×128 RGB images
- **Accuracy**: >98% on test data

## Project Structure

```
shapes-web/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ShapeDetector.tsx    # Main detection component
│   │   │   ├── ShapeDetector.css    # Component styles
│   │   │   └── HelloWorld.tsx       # Demo component
│   │   ├── App.tsx          # Root component
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── ml/
│   │   │   ├── models/
│   │   │   │   └── shape_classifier.keras  # Trained model (not in git)
│   │   │   ├── shape_classifier.py         # Model architecture
│   │   │   └── shape_generator.py          # Data generation utilities
│   │   ├── services/
│   │   │   └── shape_predictor.py          # Prediction service
│   │   └── main.py          # FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml        # Docker orchestration
└── README.md                 # This file
```

## Prerequisites

- **Node.js**: 20.19+ or 22.12+ (for frontend)
- **Python**: 3.11+ (for local backend development)
- **Docker** and **Docker Compose** (for containerized backend)
- **Git**: For version control

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/janimattiellonen/shapes-web.git
cd shapes-web
```

### 2. Set Up the Model File

⚠️ **Important**: The trained model file is not included in the repository due to its size (~100MB).

**Option A: Copy from the original Shapes project**
```bash
# If you have the original Shapes project locally
cp /path/to/Shapes/models/shape_classifier.keras backend/app/ml/models/
```

**Option B: Download from cloud storage** (if available)
```bash
# Download the model file and place it in:
# backend/app/ml/models/shape_classifier.keras
```

**Option C: Train your own model**
- See the original [Shapes project](https://github.com/janimattiellonen/shapes) for training instructions

### 3. Backend Setup (Docker - Recommended)

```bash
# Build and start the backend container
docker-compose up -d --build

# Check if backend is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# View logs
docker logs shapes-backend

# Stop the backend
docker-compose down
```

### 4. Backend Setup (Local Development - Alternative)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# The frontend will be available at http://localhost:5199
```

## Usage

### Running the Application

1. **Start the backend** (Docker):
   ```bash
   docker-compose up -d
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser** to http://localhost:5199

4. **Upload an image**:
   - Click the upload area or drag-and-drop an image
   - Supported formats: PNG, JPG, JPEG
   - Max file size: 10MB

5. **Get results**:
   - Click "Detect Shape"
   - View the detected shape with confidence scores
   - See probability distribution for all shapes

### API Endpoints

The backend provides the following endpoints:

#### `GET /`
Health check endpoint
```bash
curl http://localhost:8000/
```
Response: `{"message":"Shape Detection API is running"}`

#### `GET /health`
Detailed health status
```bash
curl http://localhost:8000/health
```
Response: `{"status":"healthy"}`

#### `POST /detect-shape`
Detect shape in uploaded image
```bash
curl -X POST http://localhost:8000/detect-shape \
  -F "image=@/path/to/image.png"
```
Response:
```json
{
  "shape": "circle",
  "confidence": 0.9999017715454102,
  "probabilities": {
    "circle": 0.9999017715454102,
    "triangle": 9.820235572988167e-05,
    "rectangle": 1.4312345752998112e-10
  }
}
```

#### `GET /docs`
Interactive API documentation (Swagger UI)
```
http://localhost:8000/docs
```

## Development

### Frontend Development

```bash
cd frontend

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests (if available)
pytest

# Format code
black app/
```

### Docker Commands

```bash
# Rebuild backend container
docker-compose up -d --build

# View logs
docker logs shapes-backend
docker logs shapes-backend --follow

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Access backend container shell
docker exec -it shapes-backend bash
```

## Configuration

### Backend Configuration

Edit `backend/app/main.py` to configure:
- CORS origins (currently set to `http://localhost:5199`)
- Model path
- Logging level

### Frontend Configuration

Edit `frontend/src/components/ShapeDetector.tsx` to configure:
- API endpoint URL
- Max file size
- Allowed file types

### Docker Configuration

Edit `docker-compose.yml` to configure:
- Port mappings
- Volume mounts
- Environment variables

## Troubleshooting

### Model file not found
**Error**: `Model file not found at backend/app/ml/models/shape_classifier.keras`

**Solution**: Ensure the model file is copied to the correct location (see Setup step 2)

### Port already in use
**Error**: `Port 8000/5199 is already in use`

**Solution**:
```bash
# Find process using the port
lsof -i :8000  # or :5199
# Kill the process
kill -9 <PID>
```

### CORS errors
**Error**: CORS policy blocks requests from frontend

**Solution**: Check that backend CORS settings in `backend/app/main.py` include your frontend URL

### Docker build fails
**Error**: Docker build fails with dependency errors

**Solution**:
```bash
# Clear Docker cache
docker-compose down
docker system prune -a
# Rebuild
docker-compose up -d --build
```

### Frontend won't compile
**Error**: TypeScript or build errors

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Performance

- **Model Loading**: ~1-2 seconds on startup (one-time cost)
- **Inference Time**: 20-50ms per image (CPU)
- **Memory Usage**: ~500MB (backend container)
- **Model Size**: ~100MB (not in git repository)

## Deployment

### Production Considerations

1. **Environment Variables**: Use environment variables for configuration
2. **Model Storage**: Store model in cloud storage (S3, GCS, etc.)
3. **Scaling**: Use multiple backend instances behind a load balancer
4. **HTTPS**: Enable SSL/TLS for production
5. **Monitoring**: Add logging and monitoring (e.g., Sentry, Prometheus)

### Build Frontend for Production

```bash
cd frontend
npm run build
# Output in dist/ directory
```

### Build Backend Docker Image

```bash
cd backend
docker build -t shapes-backend:latest .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is provided as-is for educational and research purposes.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- Machine learning with [TensorFlow](https://www.tensorflow.org/) and [Keras](https://keras.io/)
- Based on the [Shapes](https://github.com/janimattiellonen/shapes) project

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using React, FastAPI, and TensorFlow**
