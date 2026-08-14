import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PredictionResult {
  mmsi: number;
  predicted_lat_t30: number;
  predicted_lon_t30: number;
  anomaly_score: number;
}

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private readonly API_URL = 'http://localhost:8000/api/prediction';

  constructor(private http: HttpClient) {}

  predict(mmsi: number): Observable<PredictionResult> {
    return this.http.post<PredictionResult>(`${this.API_URL}/predict/${mmsi}`, {});
  }
}
