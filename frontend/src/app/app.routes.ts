import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login.component';
import { SignupComponent } from './features/signup/signup.component';
import { MapComponent } from './features/map/map.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent    },
  { path: 'signup', component: SignupComponent },
  { path: 'map', component: MapComponent },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: 'login' }
];
