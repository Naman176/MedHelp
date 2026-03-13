import axios from "axios";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_DOMAIN as string;

const fetchData = async (url: string): Promise<any> => {
  const { data } = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  return data;
};

export const postData = async (url: string, payload: any): Promise<any> => {
  const { data } = await axios.post(url, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      "Content-Type": "application/json",
    },
  });
  return data;
};

export const putData = async (url: string, payload: any): Promise<any> => {
  const { data } = await axios.put(url, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      "Content-Type": "application/json",
    },
  });
  return data;
};

export const postFormData = async (url: string, payload: FormData): Promise<any> => {
  const { data } = await axios.post(url, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return data;
};

export const patchData = async (url: string, payload: any): Promise<any> => {
  const { data } = await axios.patch(url, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
      "Content-Type": "application/json",
    },
  });
  return data;
};

export const deleteData = async(url: string): Promise<any> => {
  const data = await axios.delete(url,{
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  })
  return data
}

export default fetchData;
