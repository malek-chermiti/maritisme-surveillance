import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { SignupService } from './signup.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  private readonly fb = inject(FormBuilder);
  private readonly signupService = inject(SignupService);
  private readonly router = inject(Router);

  showPassword = false;

  signupForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    role: ['Operateur', [Validators.required]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  errorMessage = '';
  isSubmitting = false;
  roles = ['Operateur', 'Administrateur'];

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    if (this.signupForm.invalid) {
      this.signupForm.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    this.errorMessage = '';

    const payload = this.signupForm.value as {
      username: string;
      email: string;
      role: string;
      password: string;
    };

    this.signupService.signup(payload).subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (error) => {
        this.errorMessage = error?.error?.detail || 'Impossible de créer le compte.';
        this.isSubmitting = false;
      }
    });
  }
}