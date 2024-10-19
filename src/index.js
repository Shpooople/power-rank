import React from 'react';
import ReactDOM from 'react-dom/client';
import './components/index.css'; // You can create this file or ignore it if you don't need custom styles
import App from './components/app'; // This imports the main App component

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
//reportWebVitals();
