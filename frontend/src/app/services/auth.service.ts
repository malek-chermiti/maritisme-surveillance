import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, tap } from 'rxjs';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user_id: number;
}

export interface RefreshResponse {
  access_token: string;
}

export interface ValidateResponse {
  valid: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8000/api/auth';

  login(payload: LoginPayload): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.apiUrl}/login`, payload)
      .pipe(tap((response) => this.setAuthTokens(response)));
  }

  refresh(refreshToken: string): Observable<RefreshResponse> {
    return this.http
      .post<RefreshResponse>(`${this.apiUrl}/refresh`, {
        refresh_token: refreshToken
      })
      .pipe(tap((response) => this.setAccessToken(response.access_token)));
  }

  validate(token: string): Observable<ValidateResponse> {
    return this.http.post<ValidateResponse>(`${this.apiUrl}/validate`, {
      token
    });
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
  }

  get accessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  get refreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  get isLoggedIn(): boolean {
    return !!this.accessToken;
  }

  private setAuthTokens(response: AuthResponse): void {
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    localStorage.setItem('user_id', `${response.user_id}`);
  }

  private setAccessToken(token: string): void {
    localStorage.setItem('access_token', token);
  }
}
