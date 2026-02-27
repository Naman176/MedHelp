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

export default fetchData;
