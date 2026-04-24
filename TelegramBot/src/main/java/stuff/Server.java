package stuff;

import java.io.*;
import java.net.*;

public class Server {

    private static Bot bot;

    Server(Bot bot){
        Server.bot = bot;
    }

    public static void waitForResponse(Convo convo) {
        int portNumber = 12346;
        try (
                ServerSocket serverSocket = new ServerSocket(portNumber);
                Socket clientSocket = serverSocket.accept();
                PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true);
                BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
        ) {
            String responseMessage;
            StringBuilder data = new StringBuilder();
            while (true) {
                char[] buffer = new char[1024];
                int bytesRead = in.read(buffer, 0, buffer.length);
                if (bytesRead == -1) {
                    break; // End of stream
                }
                data.append(buffer, 0, bytesRead);
                String receivedMessage = data.toString();
                if (receivedMessage.contains("\r\n\r\n")) {
                    String[] messages = receivedMessage.split("\\r\\n\\r\\n", 2);
                    responseMessage = messages[0];
                    bot.sendText(convo.getUserID(), responseMessage);
                    System.out.println("Received: " + responseMessage);
                    data = new StringBuilder(messages[1]); // Keep any remaining data
                }
            }
        } catch (IOException e) {
            System.out.println("Exception caught when trying to listen on port "
                    + portNumber + " or listening for a connection");
            System.out.println(e.getMessage());
        }
    }

}