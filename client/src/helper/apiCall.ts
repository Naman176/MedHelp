import axios from "axios";

axios.defaults.baseURL = import.meta.env.VITE_SERVER_DOMAIN as string;

const fetchData = async (url: string): Promise<any> => {
  const { data } = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  console.log(data);
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

export const postFormData = async (url: string, payload: FormData): Promise<any> => {
  const { data } = await axios.post(url, payload, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return data;
};

export default fetchData;
