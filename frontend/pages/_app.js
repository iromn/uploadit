// pages/_app.js
import Head from "next/head";

function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>UploadiT - Document Q&A Bot</title>  {/* Change your tab title here */}
        <link rel="icon" href="/uploadit.png" />  {/* Favicon path */}
      </Head>
      <Component {...pageProps} />
    </>
  );
}

export default MyApp;
