import React, { ChangeEvent, useState } from 'react';
import { InlineField, Input, Select, Spinner } from '@grafana/ui';
import { QueryEditorProps, SelectableValue } from '@grafana/data';
import { DataSource } from '../datasource';
import { MyDataSourceOptions, MyQuery } from '../types';

type Props = QueryEditorProps<DataSource, MyQuery, MyDataSourceOptions>;

export function QueryEditor({ query, onChange, onRunQuery, datasource }: Props) {
  const [options, setOptions] = useState<Array<SelectableValue<string>>>([]);
  const [isLoading, setIsLoading] = useState(false);

  const onTicketIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ ...query, ticketId: event.target.value, queryType: 'panel' });
  };

  // When you click outside the Ticket ID box, it triggers this to fetch the dropdown
  const fetchDropdown = async () => {
    if (query.ticketId) {
      setIsLoading(true);
      const fetchedOptions = await datasource.getTelemetryIds(query.ticketId);
      setOptions(fetchedOptions);
      setIsLoading(false);
    }
  };

  // When you select a Telemetry ID from the dropdown, it automatically runs the graph
  const onTelemetryIdChange = (v: SelectableValue<string>) => {
    onChange({ ...query, telemetryId: v.value || '', queryType: 'panel' });
    onRunQuery(); 
  };

  return (
    <div className="gf-form-group">
      <InlineField label="Redmine Ticket ID" labelWidth={20} tooltip="Type the ID, then click outside this box to fetch Telemetry">
        <Input
          onChange={onTicketIdChange}
          value={query.ticketId || ''}
          onBlur={fetchDropdown}
          placeholder="e.g. 160310"
        />
      </InlineField>

      <InlineField label="Telemetry ID" labelWidth={20}>
        {isLoading ? (
          <Spinner />
        ) : (
          <Select
            options={options}
            value={query.telemetryId}
            onChange={onTelemetryIdChange}
            placeholder="Select a Telemetry ID..."
            width={32}
          />
        )}
      </InlineField>
    </div>
  );
}
