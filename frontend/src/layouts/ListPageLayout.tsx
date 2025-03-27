import React, { ReactNode } from 'react';
import Help from '../components/Help';
import { TooltipDirection } from '../constants';

type Props = {
  pageTitle: string;
  pageTitleHelp?: string;
  pageTitleActions?: ReactNode;
  isEmpty?: boolean;
  emptyMessage?: string;
  children: ReactNode;
};

const ListPageLayout: React.FC<Props> = (props) => {
  return (
    <div className="flex h-full justify-center">
      <div className="w-full max-w-screen-xl px-4 lg:w-4/5">
        <div className="size-full pt-8">
          <div className="flex items-end justify-between">
            <div className="flex items-center gap-2">
              <div className="text-xl font-bold">{props.pageTitle}</div>
              {props.pageTitleHelp && (
                <Help
                  direction={TooltipDirection.RIGHT}
                  message={props.pageTitleHelp}
                />
              )}
            </div>

            {props.pageTitleActions}
          </div>
          <div className="mt-2 border-b border-gray"></div>

          <div className="-mr-2 h-[calc(100%)] overflow-x-auto overflow-y-scroll border-gray scrollbar-thin scrollbar-thumb-aws-font-color-light/20 dark:scrollbar-thumb-aws-font-color-dark/20">
            <div className="h-full">
              {props.isEmpty && (
                <div className="flex size-full items-center justify-center italic text-dark-gray dark:text-light-gray">
                  {props.emptyMessage}
                </div>
              )}
              <div className="mr-2 pb-8">{props.children}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ListPageLayout;
