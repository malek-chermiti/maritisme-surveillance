import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ZoneBounds } from '../../../core/services/ingestion.service';

@Component({
  selector: 'app-zone-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './zone-dialog.component.html',
  styleUrls: ['./zone-dialog.component.css']
})
export class ZoneDialogComponent {
  @Input() zone!: ZoneBounds;
  @Output() closeDialog = new EventEmitter<void>();

  onClose(): void {
    this.closeDialog.emit();
  }
}
