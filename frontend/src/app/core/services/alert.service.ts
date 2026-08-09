import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AlertItem {
  id: number;
  mmsi: number;
  zone_name?: string | null;
  alert_level: string;
  alert_reason: string;
  distance_km?: number | null;
  anomaly_score?: number | null;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class AlertService {
  private readonly API_URL = 'http://localhost:8000/api/alert';

  constructor(private http: HttpClient) {}

  getAlerts(limit = 50): Observable<AlertItem[]> {
    return this.http.get<AlertItem[]>(`${this.API_URL}/alerts?limit=${limit}`);
  }

  getAlertsForZone(lat: number, lon: number, limit = 50): Observable<AlertItem[]> {
    return this.http.get<AlertItem[]>(`${this.API_URL}/alerts/zone?lat=${lat}&lon=${lon}&limit=${limit}`);
  }

  evaluateAlert(payload: { mmsi: number; predicted_lat_t30: number; predicted_lon_t30: number; anomaly_score: number }): Observable<any> {
    return this.http.post<any>(`${this.API_URL}/alerts/evaluate`, payload);
  }
}
