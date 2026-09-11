import { useState } from "react";
import "./App.css";

function App() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (!file) return;

    setImage(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
  };

  const analyzeBanana = async () => {
    if (!image) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      setResult(data);
    } catch (error) {
      setResult({
        error: error.message,
      });
    }

    setLoading(false);
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="logo">
          <span>🍌</span>
          BananaMath
        </div>

      </header>

      <main>
        <section className="hero">
          <div className="eyebrow">ADVANCED BANANA ANALYSIS</div>

          <h1>
            How <span>curved</span> is your banana?
          </h1>

        </section>

        <section className="upload-section">
          <label className="upload-box">
            {preview ? (
              <img src={preview} alt="Banana preview" className="preview" />
            ) : (
              <>
                <div className="upload-icon">🍌</div>

                <h2>Drop your banana here</h2>

                <p>or click to browse an image</p>

                <span className="file-types">
                  JPG, JPEG, PNG
                </span>
              </>
            )}

            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
            />
          </label>

          {preview && (
            <button
              className="analyze-button"
              onClick={analyzeBanana}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing banana...
                </>
              ) : (
                <>Analyze Banana →</>
              )}
            </button>
          )}
        </section>

        {result && !result.error && (
          <section className="results">
            <div className="section-label">YOUR RESULTS</div>

            <div className="result-card">
              <div className="score-section">
                <div className="score-label">CURVATURE SCORE</div>

                <div className="score">
                  {result.curvature}
                  <span>/100</span>
                </div>

                <div className="classification">
                  {result.classification}
                </div>
              </div>

              <div className="verdict">
                <div className="verdict-label">THE VERDICT</div>

                <p>"{result.verdict}"</p>
              </div>
            </div>

            {result.imageUrl && (
              <div className="visualization-card">
                <div>
                  <div className="section-label">CURVATURE MAP</div>
                  <h2>Proof that we actually did something</h2>
                </div>

                <img
                  src={result.imageUrl}
                  alt="Banana curvature analysis"
                />
              </div>
            )}
          </section>
        )}

        {result?.error && (
          <div className="error">
            {result.error}
          </div>
        )}
      </main>

      <footer>BananaMath</footer>
    </div>
  );
}

export default App;
