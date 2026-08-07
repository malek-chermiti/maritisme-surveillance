import { HttpErrorResponse, HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject, Injector } from '@angular/core';
import { BehaviorSubject, catchError, filter, switchMap, take, throwError } from 'rxjs';

import { AuthService } from '../../features/auth/auth.service';

let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const injector = inject(Injector);
  const accessToken = localStorage.getItem('access_token');

  let authReq = req;
  if (accessToken && !isAuthEndpoint(req.url)) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${accessToken}`
      }
    });
  }

  return next(authReq).pipe(
    catchError((error) => {
      if (
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !isAuthEndpoint(req.url)
      ) {
        const authService = injector.get(AuthService);
        return handle401Error(authReq, next, authService);
      }

      return throwError(() => error);
    })
  );
};

function isAuthEndpoint(url: string): boolean {
  const normalizedUrl = url.toLowerCase();

  return (
    normalizedUrl.includes('/api/auth/login') ||
    normalizedUrl.includes('/api/auth/refresh') ||
    normalizedUrl.includes('/api/auth/validate') ||
    normalizedUrl.includes('/oauth/login') ||
    normalizedUrl.includes('/oauth/refresh')
  );
}

function handle401Error(req: HttpRequest<unknown>, next: HttpHandlerFn, authService: AuthService) {
  if (!isRefreshing) {
    isRefreshing = true;
    refreshTokenSubject.next(null);

    const refreshToken = authService.refreshToken;

    if (!refreshToken) {
      isRefreshing = false;
      authService.logout();
      return throwError(() => new HttpErrorResponse({ status: 401, statusText: 'No refresh token available' }));
    }

    return authService.refresh(refreshToken).pipe(
      switchMap((response) => {
        isRefreshing = false;

        const newAccessToken = response.access_token;
        localStorage.setItem('access_token', newAccessToken);
        refreshTokenSubject.next(newAccessToken);

        return next(req.clone({
          setHeaders: { Authorization: `Bearer ${newAccessToken}` }
        }));
      }),
      catchError((refreshError) => {
        isRefreshing = false;
        refreshTokenSubject.next(null);
        authService.logout();
        return throwError(() => refreshError);
      })
    );
  }

  return refreshTokenSubject.pipe(
    filter((token): token is string => token !== null),
    take(1),
    switchMap((token) =>
      next(req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      }))
    )
  );
}
