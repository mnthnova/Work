import React, { ChangeEvent } from 'react';
import { InlineField, Input } from '@grafana/ui';
import { QueryEditorProps } from '@grafana/data';
import { DataSource } from '../datasource';
import { MyDataSourceOptions, MyQuery } from '../types';

type Props = QueryEditorProps<DataSource, MyQuery, MyDataSourceOptions>;

export function QueryEditor({ query, onChange, onRunQuery }: Props) {
  const onTicketIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ ...query, ticketId: event.target.value, queryType: 'panel' });
  };

  const onTelemetryIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ ...query, telemetryId: event.target.value, queryType: 'panel' });
  };

  return (
    <div className="gf-form-group">
      <InlineField label="Redmine Ticket ID" labelWidth={20} tooltip="e.g. 160310">
        <Input onChange={onTicketIdChange} value={query.ticketId || ''} onBlur={onRunQuery} />
      </InlineField>
      <InlineField label="Telemetry ID" labelWidth={20} tooltip="Type your variable here, e.g. $telemetry_id">
        <Input onChange={onTelemetryIdChange} value={query.telemetryId || ''} onBlur={onRunQuery} />
      </InlineField>
    </div>
  );
}






import React, { useState } from 'react';
import { InlineField, Input } from '@grafana/ui';
import { MyVariableQuery } from '../types';

interface VariableQueryProps {
  query: MyVariableQuery;
  onChange: (query: MyVariableQuery, definition: string) => void;
}

export const VariableQueryEditor = ({ onChange, query }: VariableQueryProps) => {
  const [state, setState] = useState(query.ticketId || '');

  const saveQuery = () => {
    onChange({ ticketId: state }, `Ticket ID: ${state}`);
  };

  return (
    <div className="gf-form">
      <InlineField label="Ticket ID for Dropdown" labelWidth={25}>
        <Input
          name="ticketId"
          value={state}
          onChange={(e) => setState(e.currentTarget.value)}
          onBlur={saveQuery}
          placeholder="e.g. 160310"
        />
      </InlineField>
    </div>
  );
};
