import React, { useEffect, useState } from "react";
import fetchData, { deleteData } from "../helper/apiCall";
import toast from "react-hot-toast";
import { Trash2, UserCheck, UserX } from "lucide-react";
import "../styles/userManagement.css";

import type { UserAdminView } from "../types";

const AllUsers: React.FC = () => {
  const [users, setUsers] = useState<UserAdminView[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    try {
      // Endpoint: GET /users/
      const data = await fetchData("/admin/users/");
      
      // Map API snake_case to frontend camelCase
      const mapped: UserAdminView[] = data.map((user: any) => ({
        id: user.id,
        firstName: user.firstname,
        lastName: user.lastname,
        email: user.email,
        role: user.role,
        isActive: user.is_active,
        isVerified: user.is_verified,
        createdAt: user.created_at,
      }));

      setUsers(mapped);
    } catch (error) {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDelete = async (userId: string, userEmail: string) => {
    const confirm = window.confirm(
      `Are you sure you want to permanently delete user: ${userEmail}? This cannot be undone.`
    );
    
    if (!confirm) return;

    const loadingToast = toast.loading("Deleting user...");
    try {
      // Endpoint: DELETE /users/{user_id}
      await deleteData(`/admin/users/${userId}`);
      toast.success("User deleted successfully", { id: loadingToast });
      
      // Update UI by filtering out the deleted user
      setUsers((prev) => prev.filter((user) => user.id !== userId));
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Deletion failed", { id: loadingToast });
    }
  };

  if (loading) return <div className="loader">Loading users...</div>;

  return (
    <div className="user-management-container">
      <div className="management-header">
        <h2>User Accounts</h2>
        <span className="count-badge">{users.length} Users</span>
      </div>

      <div className="table-responsive">
        <table className="user-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.length > 0 ? (
              users.map((user) => (
                <tr key={user.id}>
                  <td>
                    {user.firstName} {user.lastName}
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role-badge ${user.role}`}>
                      {user.role.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {user.isActive ? (
                      <span className="status-active"><UserCheck size={16}/> Active</span>
                    ) : (
                      <span className="status-inactive"><UserX size={16}/> Inactive</span>
                    )}
                  </td>
                  <td>
                    <button 
                      className="btn-delete" 
                      onClick={() => handleDelete(user.id, user.email)}
                      title="Delete User"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="no-data">No users found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AllUsers;