// src/lib/axiosConfig.js
import axios from "axios";

const isProd = window.location.hostname === "entropy157.com";

const baseURL = isProd
  ? "https://entropy157.com"
  : window.location.protocol + "//" + window.location.host;

export default axios.create({
  baseURL,
});
