import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ZoneBounds {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
}

export interface VesselPosition {
  mmsi: number;
  lat: number;
  lon: number;
  speed: number;
  heading: number;
  recorded_at: string;
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

  getVesselsInZone(zone: ZoneBounds): Observable<VesselPosition[]> {
    const params = {
      lat_min: zone.lat_min.toString(),
      lat_max: zone.lat_max.toString(),
      lon_min: zone.lon_min.toString(),
      lon_max: zone.lon_max.toString()
    };
    return this.http.get<VesselPosition[]>(`${this.API_URL}/in-zone`, { params });
  }
}
