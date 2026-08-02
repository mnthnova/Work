def ExecuteCommand(self, request, context):
        print(f"[RECEIVED] ExecuteCommand for ID: '{request.commandId}'")
        
        # 1. We create some fake database log data for your timeline
        fake_timeline_data = [
            {"Time": "12:00:00", "BE_State": "NORMAL", "Thermal_Throttle": None, "FWQ": None},
            {"Time": "12:05:00", "BE_State": "WARNING", "Thermal_Throttle": "THROTTLED", "FWQ": "FWQ_BE_Response"},
            {"Time": "12:10:00", "BE_State": "CRITICAL", "Thermal_Throttle": "THROTTLED", "FWQ": None}
        ]
        
        # 2. We convert it to a JSON string just like your production code does
        json_string = json.dumps(fake_timeline_data, indent=2)
        print("[SENDING] Fake JSON Timeline Data back to Grafana...")

        # 3. We pack it into the SyncResponse
        sync_resp = commands_pb2.Command.Execute.SyncResponse(
            status=200,
            respData=json_string,
            downloadAvailable=False
        )
        
        return commands_pb2.Command.Execute.Response(syncResponse=sync_resp)
