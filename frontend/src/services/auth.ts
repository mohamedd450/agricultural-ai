import { login as apiLogin, TokenResponse } from "./api";

const TOKEN_KEY = "auth_token";

interface TokenPayload {
  sub: string;
  exp: number;
  [key: string]: unknown;
}

class AuthService {
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await apiLogin(username, password);
    localStorage.setItem(TOKEN_KEY, response.access_token);
    return response;
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      const payload = this.decodeToken(token);
      if (!payload) return false;
      // Check expiry (exp is in seconds, Date.now() in ms)
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  getUser(): TokenPayload | null {
    const token = this.getToken();
    if (!token) return null;
    return this.decodeToken(token);
  }

  // ── Private ─────────────────────────────────────────────────────────────

  private decodeToken(token: string): TokenPayload | null {
    try {
      const base64Url = token.split(".")[1];
      if (!base64Url) return null;
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
      return JSON.parse(jsonPayload) as TokenPayload;
    } catch {
      return null;
    }
  }
}

const authService = new AuthService();
export default authService;
