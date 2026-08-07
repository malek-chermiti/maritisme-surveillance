import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ZoneBounds {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
}

@Injectable({
  providedIn: 'root'
})
export class IngestionService {
  private readonly API_URL = 'http://localhost:8000/api/ingestion/vessels';

  constructor(private http: HttpClient) {}

  getZone(): Observable<ZoneBounds> {
    return this.http.get<ZoneBounds>(`${this.API_URL}/zone`);
  }

  updateZone(zone: ZoneBounds): Observable<ZoneBounds> {
    return this.http.put<ZoneBounds>(`${this.API_URL}/zone`, zone);
  }
}
