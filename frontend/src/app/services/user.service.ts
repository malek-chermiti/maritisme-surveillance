import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface SignupPayload {
  username: string;
  email: string;
  password: string;
  role: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8000/api/users';

  signup(payload: SignupPayload): Observable<unknown> {
    return this.http.post<unknown>(`${this.apiUrl}/users`, payload);
  }
}
