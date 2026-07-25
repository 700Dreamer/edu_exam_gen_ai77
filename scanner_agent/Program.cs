using System;
using System.Net;
using System.Text;
using System.Threading;
using System.Collections.Generic;

namespace ScannerAgent
{
    class Program
    {
        static void Main(string[] args)
        {
            string url = "http://127.0.0.1:8181/";
            
            using (HttpListener listener = new HttpListener())
            {
                listener.Prefixes.Add(url);
                try
                {
                    listener.Start();
                    Console.WriteLine("Scanner Agent HTTP Server started on " + url);
                    Console.WriteLine("Listening for direct browser requests...");
                }
                catch (HttpListenerException ex)
                {
                    Console.WriteLine("Failed to start server: " + ex.Message);
                    Console.WriteLine("You may need to run this as Administrator to bind to the port.");
                    return;
                }

                while (true)
                {
                    try
                    {
                        HttpListenerContext context = listener.GetContext();
                        ThreadPool.QueueUserWorkItem((state) =>
                        {
                            try { ProcessRequest((HttpListenerContext)state); }
                            catch (Exception e) { Console.WriteLine("Error processing request: " + e.Message); }
                        }, context);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine("Error accepting request: " + ex.Message);
                    }
                }
            }
        }

        static void ProcessRequest(HttpListenerContext context)
        {
            HttpListenerRequest request = context.Request;
            HttpListenerResponse response = context.Response;

            // Handle CORS for all origins (or restrict to edulytics.net in production)
            response.AppendHeader("Access-Control-Allow-Origin", "*");
            response.AppendHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
            response.AppendHeader("Access-Control-Allow-Headers", "Content-Type");

            if (request.HttpMethod == "OPTIONS")
            {
                response.StatusCode = 200;
                response.Close();
                return;
            }

            if (request.Url.AbsolutePath == "/devices" && request.HttpMethod == "GET")
            {
                Console.WriteLine("Devices requested by browser...");
                string json = "{" +
                              "\"sane_installed\":false," +
                              "\"platform\":\"Windows\"," +
                              "\"devices\":[{\"device_id\":\"Agent_Scanner_001\",\"model\":\"Local Hardware Scanner\",\"vendor\":\"ScannerAgent\"}]" +
                              "}";
                
                byte[] buffer = Encoding.UTF8.GetBytes(json);
                response.ContentType = "application/json";
                response.ContentLength64 = buffer.Length;
                using (System.IO.Stream output = response.OutputStream)
                {
                    output.Write(buffer, 0, buffer.Length);
                }
                response.Close();
                return;
            }

            if (request.Url.AbsolutePath == "/scan" && request.HttpMethod == "POST")
            {
                Console.WriteLine("Scan request received from browser...");
                
                // TODO: Replace with native TWAIN/WIA continuous scan loop.
                // Simulating a hardware scan of two pages for now.
                
                List<string> base64Images = new List<string>();
                for (int i = 1; i <= 2; i++)
                {
                    Console.WriteLine("Scanning physical page " + i + "...");
                    Thread.Sleep(1500); // Simulate scanning delay
                    
                    // Dummy JPEG representation (1x1 transparent/black pixel)
                    byte[] dummyJpeg = new byte[] { 0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0x37, 0xFF, 0xD9 };
                    
                    base64Images.Add("\"" + Convert.ToBase64String(dummyJpeg) + "\"");
                }

                // Construct JSON response natively
                string json = "{" +
                              "\"status\":\"success\"," +
                              "\"image_base64_list\":[" + string.Join(",", base64Images) + "]" +
                              "}";

                byte[] buffer = Encoding.UTF8.GetBytes(json);
                response.ContentType = "application/json";
                response.ContentLength64 = buffer.Length;
                
                using (System.IO.Stream output = response.OutputStream)
                {
                    output.Write(buffer, 0, buffer.Length);
                }
                response.Close();
                Console.WriteLine("Scan payload sent to browser.");
            }
            else
            {
                response.StatusCode = 404;
                response.Close();
            }
        }
    }
}
