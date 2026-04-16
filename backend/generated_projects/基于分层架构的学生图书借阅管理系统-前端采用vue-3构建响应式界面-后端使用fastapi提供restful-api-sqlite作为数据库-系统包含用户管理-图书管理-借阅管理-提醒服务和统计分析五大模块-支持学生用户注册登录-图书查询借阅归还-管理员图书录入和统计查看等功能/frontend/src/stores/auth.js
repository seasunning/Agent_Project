import { defineStore } from 'pinia';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        token: localStorage.getItem('token') || null,
        isAuthenticated: !!localStorage.getItem('token'),
    }),

    getters: {
        getUser: (state) => state.user,
        getToken: (state) => state.token,
        isLoggedIn: (state) => state.isAuthenticated,
    },

    actions: {
        async login(credentials) {
            try {
                const response = await axios.post(`${API_BASE_URL}/api/auth/login`, credentials);
                const { access_token, user } = response.data;
                this.token = access_token;
                this.user = user;
                this.isAuthenticated = true;
                localStorage.setItem('token', access_token);
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                return { success: true, user };
            } catch (error) {
                console.error('Login failed:', error);
                return { success: false, error: error.response?.data?.detail || 'Login failed' };
            }
        },

        async register(userData) {
            try {
                const response = await axios.post(`${API_BASE_URL}/api/auth/register`, userData);
                const { access_token, user } = response.data;
                this.token = access_token;
                this.user = user;
                this.isAuthenticated = true;
                localStorage.setItem('token', access_token);
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                return { success: true, user };
            } catch (error) {
                console.error('Registration failed:', error);
                return { success: false, error: error.response?.data?.detail || 'Registration failed' };
            }
        },

        logout() {
            this.user = null;
            this.token = null;
            this.isAuthenticated = false;
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
        },

        async fetchUserProfile() {
            if (!this.token) return;
            try {
                const response = await axios.get(`${API_BASE_URL}/api/auth/me`);
                this.user = response.data;
            } catch (error) {
                console.error('Failed to fetch user profile:', error);
                this.logout();
            }
        },

        initializeAuth() {
            const token = localStorage.getItem('token');
            if (token) {
                this.token = token;
                this.isAuthenticated = true;
                axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                this.fetchUserProfile();
            }
        },
    },
});
