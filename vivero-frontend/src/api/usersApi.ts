import api from "./axiosInstance";

export const getUsers = () => api.get("/users").then((res) => res.data.data);

export const updateUser = (
  userId: number,
  payload: {
    firstName: string;
    lastName: string;
    email: string;
    phoneNumber?: string | null;
    role?: "ADMIN" | "CONTROLLER" | "VIEWER" | null;
    active?: boolean | null;
  }
) => api.patch(`/users/${userId}`, payload).then((res) => res.data.data);

export const updateUserPassword = (userId: number, password: string) =>
  api.patch(`/users/${userId}/password`, { password }).then((res) => res.data.data);

export const deleteUser = (userId: number) => api.delete(`/users/${userId}`).then((res) => res.data.data);
