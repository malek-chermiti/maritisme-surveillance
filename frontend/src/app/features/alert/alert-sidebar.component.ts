import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlertItem } from '../../core/services/alert.service';

@Component({
  selector: 'app-alert-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './alert-sidebar.component.html',
  styleUrls: ['./alert-sidebar.component.css']
})
export class AlertSidebarComponent {
  @Input() alerts: AlertItem[] = [];
  @Input() zoneName: string | null = null;
  @Input() activeTab = 'alerts';
  @Output() loadAlerts = new EventEmitter<void>();

  onAlertTabClick(): void {
    this.loadAlerts.emit();
  }
}
