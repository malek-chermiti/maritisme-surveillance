import { Component, AfterViewInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { IngestionService, ZoneBounds } from '../../core/services/ingestion.service';

declare const L: any; // use global Leaflet loaded via angular.json scripts

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements AfterViewInit, OnDestroy {
  private map: any;
  private drawnItems: any;
  private isBrowser: boolean;

  statusMessage = '';
  isSaving = false;

  constructor(
    private ingestionService: IngestionService,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngAfterViewInit(): void {
    if (!this.isBrowser) {
      return;
    }

    this.initMap();
    this.loadExistingZone();
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
    }
  }

  private initMap(): void {
    this.map = L.map('map').setView([35.0, 10.0], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    const drawControl = new L.Control.Draw({
      draw: {
        rectangle: true,
        polygon: false,
        circle: false,
        marker: false,
        polyline: false,
        circlemarker: false
      },
      edit: {
        featureGroup: this.drawnItems
      }
    });
    this.map.addControl(drawControl);

    this.map.on(L.Draw.Event.CREATED, (event: any) => {
      this.drawnItems.clearLayers();
      const layer = event.layer;
      this.drawnItems.addLayer(layer);
      this.onZoneDrawn(layer);
    });

    this.map.on(L.Draw.Event.EDITED, (event: any) => {
      const layers = event.layers;
      layers.eachLayer((layer: any) => {
        this.onZoneDrawn(layer);
      });
    });
  }

  private loadExistingZone(): void {
    this.ingestionService.getZone().subscribe({
      next: (zone) => {
        this.drawZoneOnMap(zone);
      },
      error: () => {
        this.statusMessage = 'Aucune zone existante trouvée.';
      }
    });
  }

  private drawZoneOnMap(zone: ZoneBounds): void {
    const bounds = L.latLngBounds(
      [zone.lat_min, zone.lon_min],
      [zone.lat_max, zone.lon_max]
    );

    this.drawnItems.clearLayers();
    const rectangle = L.rectangle(bounds, { color: '#2563eb', weight: 2 });
    this.drawnItems.addLayer(rectangle);
    this.map.fitBounds(bounds);
  }

  private onZoneDrawn(layer: any): void {
    const bounds = layer.getBounds();

    const zone: ZoneBounds = {
      lat_min: bounds.getSouth(),
      lat_max: bounds.getNorth(),
      lon_min: bounds.getWest(),
      lon_max: bounds.getEast()
    };

    this.saveZone(zone);
  }

  private saveZone(zone: ZoneBounds): void {
    this.isSaving = true;
    this.statusMessage = '';

    this.ingestionService.updateZone(zone).subscribe({
      next: () => {
        this.isSaving = false;
        this.statusMessage = 'Zone mise à jour avec succès.';
      },
      error: () => {
        this.isSaving = false;
        this.statusMessage = 'Erreur lors de la mise à jour de la zone.';
      }
    });
  }
}
