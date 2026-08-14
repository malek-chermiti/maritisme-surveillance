import { Component, AfterViewInit, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { IngestionService, ZoneBounds } from '../../core/services/ingestion.service';
import { AlertService, AlertItem } from '../../core/services/alert.service';
import { PredictionService } from '../../core/services/prediction.service';
import { ZoneDialogComponent } from './zone-dialog/zone-dialog.component';
import { AlertSidebarComponent } from '../alert/alert-sidebar.component';

declare const L: any; // use global Leaflet loaded via angular.json scripts

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, ZoneDialogComponent, AlertSidebarComponent],
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements AfterViewInit, OnDestroy {
  private map: any;
  private drawnItems: any;
  private isBrowser: boolean;

  statusMessage = '';
  isSaving = false;
  showDialog = false;
  dialogZone: ZoneBounds | null = null;
  showSidebar = true;
  selectedZoneLabel = 'Zone active';
  alerts: AlertItem[] = [];

  constructor(
    private ingestionService: IngestionService,
    private alertService: AlertService,
    private predictionService: PredictionService,
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
        this.fetchAlertsForZone(zone);
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
    this.dialogZone = zone;
    this.showDialog = true;
    this.fetchAlertsForZone(zone);
  }

  private fetchAlertsForZone(zone: ZoneBounds): void {
    const centerLat = (zone.lat_min + zone.lat_max) / 2;
    const centerLon = (zone.lon_min + zone.lon_max) / 2;
    this.selectedZoneLabel = 'Zone sélectionnée';
    this.statusMessage = 'Recherche des navires dans la zone...';
    this.showSidebar = true;
    this.alerts = [];

    this.ingestionService.getVesselsInZone(zone).subscribe({
      next: (vessels) => {
        if (vessels.length === 0) {
          this.statusMessage = 'Aucun navire dans cette zone.';
          return;
        }

        this.statusMessage = `Analyse de ${vessels.length} navire(s)...`;

        const refreshAlertsImmediately = () => {
          this.loadAlertsForCenter(centerLat, centerLon);
        };

        vessels.forEach((vessel) => {
          this.predictionService.predict(vessel.mmsi)
            .pipe(catchError(() => of(null)))
            .subscribe({
              next: refreshAlertsImmediately,
              error: refreshAlertsImmediately
            });
        });
      },
      error: () => {
        this.statusMessage = 'Erreur lors de la récupération des navires.';
      }
    });
  }

  private loadAlertsForCenter(lat: number, lon: number): void {
    this.statusMessage = 'Chargement des alertes...';

    this.alertService.getAlertsForZone(lat, lon).subscribe({
      next: (alerts) => {
        const uniqueAlerts = alerts.filter((alert, index, list) => {
          const key = [
            alert.mmsi,
            alert.zone_name ?? '',
            alert.alert_level,
            alert.alert_reason,
            alert.distance_km ?? '',
            alert.anomaly_score ?? ''
          ].join('|');

          return list.findIndex((candidate) => {
            const candidateKey = [
              candidate.mmsi,
              candidate.zone_name ?? '',
              candidate.alert_level,
              candidate.alert_reason,
              candidate.distance_km ?? '',
              candidate.anomaly_score ?? ''
            ].join('|');

            return candidateKey === key;
          }) === index;
        }).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

        this.alerts = uniqueAlerts;
        if (this.alerts.length > 0 && this.alerts[0].zone_name) {
          this.selectedZoneLabel = this.alerts[0].zone_name;
        }
        this.statusMessage = this.alerts.length === 0 ? 'Aucune alerte trouvée pour cette zone.' : '';
      },
      error: () => {
        this.statusMessage = 'Erreur lors du chargement des alertes.';
      }
    });
  }

  reloadAlerts(): void {
    if (!this.dialogZone) {
      return;
    }
    this.fetchAlertsForZone(this.dialogZone);
  }

  closeDialog(): void {
    this.showDialog = false;
  }

  openZoneDetails(): void {
    if (this.dialogZone) {
      this.showDialog = true;
      return;
    }

    this.ingestionService.getZone().subscribe({
      next: (zone) => {
        this.dialogZone = zone;
        this.showDialog = true;
      },
      error: () => {
        this.statusMessage = 'Aucune zone existante trouvée.';
      }
    });
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
