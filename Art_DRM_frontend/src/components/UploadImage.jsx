// import { useState } from "react";
// import axios from "axios";

// export default function UploadImage() {
//   const [file, setFile] = useState(null);
//   const [preview, setPreview] = useState(null);
//   const [status, setStatus] = useState("");
//   const [loading, setLoading] = useState(false);

//   const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

//   function onFileChange(e) {
//     const f = e.target.files?.[0];
//     setFile(f || null);
//     setStatus("");
//     if (f) {
//       const url = URL.createObjectURL(f);
//       setPreview(url);
//     } else {
//       setPreview(null);
//     }
//   }

//   async function onSubmit(e) {
//     e.preventDefault();
//     if (!file) {
//       setStatus("Please choose an image first.");
//       return;
//     }
//     setLoading(true);
//     setStatus("");

//     try {
//       const formData = new FormData();
//       formData.append("file", file);

//       const res = await axios.post(`${apiBase}/api/images/upload`, formData, {
//         headers: { "Content-Type": "multipart/form-data" },
//       });

//       const d = res.data;
//       if (d.status === "duplicate_exact") {
//         setStatus(`Duplicate: this exact image already exists (id: ${d.imageId}).`);
//       } else if (d.status === "created") {
//         setStatus(`Success: stored new image (id: ${d.imageId}).`);
//       }else if (d.status === "duplicate_perceptual") {
//         setStatus(`Duplicate: this perceptual image already exists (id: ${d.imageId}).`);
//       }else if (d.status === "duplicate_ai") {
//         setStatus(`Duplicate: this CNN image already exists (id: ${d.imageId}).`);
//       }  
//       else {
//         setStatus("Unexpected response.");
//       }
//     } catch (err) {
//       const msg = err?.response?.data?.detail || err.message;
//       setStatus(`Error: ${msg}`);
//     } finally {
//       setLoading(false);
//     }
//   }

//   return (
//     <div style={{ maxWidth: 520, margin: "2rem auto", fontFamily: "system-ui" }}>
//       <h2>Upload Image</h2>
//       <form onSubmit={onSubmit}>
//         <input
//           type="file"
//           accept="image/*"
//           onChange={onFileChange}
//           disabled={loading}
//         />
//         <div style={{ margin: "1rem 0" }}>
//           {preview && (
//             <img
//               src={preview}
//               alt="preview"
//               style={{ maxWidth: "100%", borderRadius: 8 }}
//             />
//           )}
//         </div>
//         <button type="submit" disabled={loading || !file}>
//           {loading ? "Uploading..." : "Upload"}
//         </button>
//       </form>
//       {status && (
//         <p style={{ marginTop: "1rem" }}>
//           {status}
//         </p>
//       )}
//     </div>
//   );
// }



import { useState } from "react";
import axios from "axios";

export default function UploadImage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState("gemini-1.5-flash"); 

  const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  function onFileChange(e) {
    const f = e.target.files?.[0];
    setFile(f || null);
    setStatus("");
    if (f) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!file) {
      setStatus("Please choose an image first.");
      return;
    }
    setLoading(true);
    setStatus("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_name", model); 

      const res = await axios.post(`${apiBase}/api/images/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const d = res.data;
      if (d.status === "duplicate_exact") {
        setStatus(`Duplicate: this exact image already exists (id: ${d.imageId}).`);
      } else if (d.status === "created") {
        setStatus(`Success: stored new image (id: ${d.imageId}).`);
      } else if (d.status === "duplicate_perceptual") {
        setStatus(`Duplicate: this perceptual image already exists (id: ${d.imageId}).`);
      } else if (d.status === "duplicate_ai") {
        setStatus(`Duplicate: this CNN image already exists (id: ${d.imageId}).`);
      } else if (d.status === "rejected_ai") {
        setStatus(`Classified as an AI generated image:\n${d.description}`);
      } else {
        setStatus("Unexpected response.");
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message;
      setStatus(`Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 520, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h2>Upload Image</h2>
      <form onSubmit={onSubmit}>
        <input
          type="file"
          accept="image/*"
          onChange={onFileChange}
          disabled={loading}
        />

        
        <div style={{ margin: "1rem 0" }}>
          <label>Select Model: </label>
          <select value={model} onChange={(e) => setModel(e.target.value)} disabled={loading}>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="openai-gpt4.1">OpenAI GPT-4.1</option>
            <option value="groq-llama-3.3-70b">Groq Llama-3.3 70B</option>
            <option value="groq-gpt-oss-20b">Groq GPT-OSS-20B</option>
          </select>
        </div>

        <div style={{ margin: "1rem 0" }}>
          {preview && (
            <img
              src={preview}
              alt="preview"
              style={{ maxWidth: "100%", borderRadius: 8 }}
            />
          )}
        </div>
        <button type="submit" disabled={loading || !file}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {status && <p style={{ marginTop: "1rem" }}>{status}</p>}
    </div>
  );
}
