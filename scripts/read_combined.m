%% check that we plot the same results

clearvars
% selfolder = dir('./session*');
close all

sessions = dir('../data/unsynced-t*');

sessions = sessions([sessions.isdir]);

roles = {'sender', 'receiver'};

for i=1:size(sessions, 1)
    
    text = fileread(['../data/' sessions(i).name '/combined.json']);
    A = jsondecode(text);
    plyr = A(contains( cellfun( @(sas) sas.component, A, 'uni', false ), 'PointBufferRenderer'));
    
    figure
    for j=1:size(roles,2)
        sessiontime =  cell2mat(cellfun( @(sas) sas.sessiontime, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
        
        pc_latency =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
        
%         yyaxis left
        plot(sessiontime, pc_latency, 'LineWidth', 1.4);
        
        hold on
        ylabel('latency [ms]');
        ylim([0 1000]);
        
        if j==3
            yyaxis right
            max_queuesize =  cell2mat(cellfun( @(sas) sas.max_queuesize, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            plot(sessiontime, max_queuesize, 'LineWidth', 1.4)
            ylabel('max\_queue');
        end
        
        
        %             if size(avg_queuesize) == size(sessiontime)
        %                 plot(sessiontime, avg_queuesize)
        %             end
        
    end
    legend(roles)
set(gca, 'FontSize', 14);

end


%% check that we plot the same results

clearvars
% selfolder = dir('./session*');
close all

sessions = dir('../data/unsynced*');

sessions = sessions([sessions.isdir]);

roles = {'sender', 'receiver'};

for i=size(sessions, 1)
    
    text = fileread(['../data/' sessions(i).name '/combined.json']);
    A = jsondecode(text);
    plyr = A(strcmp( cellfun( @(sas) sas.component, A, 'uni', false ), 'PerformanceStats' ));
    
    
    for j=1:size(roles,2)
        sessiontime =  cell2mat(cellfun( @(sas) sas.sessiontime, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
        
%         pc_latency =  cell2mat(cellfun( @(sas) sas.pc_latency_ms, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
        
%         yyaxis left
%         plot(sessiontime, pc_latency, 'LineWidth', 1.4);
%         
%         hold on
%         ylabel('latency [ms]');
%         ylim([0 1000]);
        
%          if j==2
%             yyaxis right

%             perfstats = A(strcmp(cellfun(@(sas) sas.component, A, 'uni', false), 'PerformanceStats'));
            cpu_use =  cell2mat(cellfun( @(sas) sas.cpu, plyr(strcmp(cellfun(@(sas) sas.role, plyr, 'uni', false), roles{j})), 'uni', false ));
            plot(sessiontime, cpu_use, 'LineWidth', 1.4)
            ylabel('cpu\_usage');
            hold on
%          end
        
        
        %             if size(avg_queuesize) == size(sessiontime)
        %                 plot(sessiontime, avg_queuesize)
        %             end
        
    end
end

legend(roles)
set(gca, 'FontSize', 14);