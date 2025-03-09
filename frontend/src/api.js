import axios from "axios";

const API_URL = "http://192.168.1.6:3000/";

// Função para validar a sequência
export async function validateSequence(sessionId, sequence) {
  // Transforma a lista de números individuais em pares
  const formattedSequence = sequence.map(num => [num]);

  console.log("🔍 Enviando para o backend:", {
      session_id: sessionId,
      sequence: formattedSequence
  });

  try {
      const response = await axios.post("http://127.0.0.1:8000/validate_sequence", {
          session_id: sessionId,
          sequence: formattedSequence
      }, {
          headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`
          }
      });

      console.log("✅ Resposta do backend:", response.data);
      return response.data;
  } catch (error) {
      console.error("❌ Erro ao validar sequência:", error);
      throw error;
  }
}

// Outras funções da API
export async function generateSession(username) {
    const response = await axios.post(`${API_URL}/generate_session`, { username });
    return response.data;
}

export async function invalidateSession(sessionId) {
    const response = await axios.post(`${API_URL}/invalidate_session`, { session_id: sessionId });
    return response.data;
}

export async function registerUser(username, password) {
    const response = await axios.post(`${API_URL}/register`, { username, password });
    return response.data;
}