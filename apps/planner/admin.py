from datetime import timedelta, datetime, date

from django import forms
from django.contrib import admin
from django.contrib.admin.filters import AllValuesFieldListFilter
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from daterangefilter.filters import DateRangeFilter

from apps.planner.models import TimePlan, TimeLog, TeamMember, Project, Tech, Team, ProjectManager, ProjectState, \
    TimePlanSummary, TimeLogSummary


def get_all_weeks():
    weeks = []
    week_index = 1
    week_today = int(datetime.now().date().strftime("%V"))
    start_date = date.today().replace(month=1, day=1)
    start_week = start_date - timedelta(days=start_date.weekday())

    while True:
        current_week = start_week + timedelta(days=7 * week_index)

        if current_week.year > start_date.year:
            break

        if week_index == week_today - 1:
            indicator = ' (prev)'
        elif week_index == week_today:
            indicator = ' (this)'
        elif week_index == week_today + 1:
            indicator = ' (next)'
        else:
            indicator = ''

        weeks.append(
            (current_week, f'{current_week}  #{week_index}' + indicator)
        )

        week_index += 1
    return weeks


class PlanInlineFormSet(BaseInlineFormSet):
    def get_queryset(self):
        qs = super(PlanInlineFormSet, self).get_queryset()
        return qs.order_by('week')


class WeekChoiceForm(forms.ModelForm):
    DATE_CHOICES = get_all_weeks()

    week = forms.ChoiceField(choices=DATE_CHOICES)


class TimePlanInline(admin.TabularInline):
    model = TimePlan
    formset = PlanInlineFormSet
    form = WeekChoiceForm
    extra = 0


class TimeLogInline(admin.TabularInline):
    model = TimeLog
    formset = PlanInlineFormSet
    form = WeekChoiceForm
    extra = 0


class TeamMembersInline(admin.TabularInline):
    model = TeamMember
    extra = 0


@admin.register(TimePlan)
class TimePlanAdmin(admin.ModelAdmin):
    form = WeekChoiceForm
    list_display = ['project', 'tech', 'week', 'time']
    list_filter = (
        ('week', DateRangeFilter),
        'project__name',
        'tech__name',
    )
    search_fields = (
        'project',
        'tech',
        'time',
    )


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    form = WeekChoiceForm
    list_display = ['project', 'member', 'week', 'time']
    list_filter = (
        ('week', DateRangeFilter),
        'project__name',
        'member__team__name',
    )
    search_fields = (
        'project',
        'member',
        'time',
    )


@admin.register(TimePlanSummary)
class TimePlanSummaryAdmin(admin.ModelAdmin):
    list_display = ['project', 'pm_responsabil', 'state', 'week', 'back_end', 'front_end', 'mobile', 'analiza',
                    'project_manager_planned', 'team_leads_logged', 'fact', 'difference']
    list_filter = (
        ('week', DateRangeFilter),
        'project__state',
        'project__manager__fullname',
        ('project__name', AllValuesFieldListFilter),
    )
    search_fields = (
        'project__name',
    )

    def get_queryset(self, request):
        qs = super(TimePlanSummaryAdmin, self).get_queryset(request)
        qs = qs.order_by('-week', 'project').distinct('project', 'week')
        return qs

    @classmethod
    def pm_responsabil(cls, instance: TimePlanSummary):
        return instance.project.manager.fullname

    @classmethod
    def state(cls, instance: TimePlanSummary):
        return instance.project.state.name

    @classmethod
    def back_end(cls, instance: TimePlanSummary):
        return instance.get_back_end()

    @classmethod
    def front_end(cls, instance: TimePlanSummary):
        return instance.get_front_end()

    @classmethod
    def mobile(cls, instance: TimePlanSummary):
        return instance.get_mobile()

    @classmethod
    def analiza(cls, instance: TimePlanSummary):
        return instance.get_analiza()

    @classmethod
    def project_manager_planned(cls, instance: TimePlanSummary):
        return instance.get_time_planned()

    @classmethod
    def team_leads_logged(cls, instance: TimePlanSummary):
        return instance.get_time_logged()

    @classmethod
    def fact(cls, instance: TimePlanSummary):
        return instance.get_in_fact()

    @classmethod
    def difference(cls, instance: TimePlanSummary):
        return instance.get_difference()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TimeLogSummary)
class TimeLogSummaryAdmin(admin.ModelAdmin):
    list_display = ['team', 'members', 'projects', 'week', 'project_manager_planned', 'team_lead_logged', 'team_work',
                    'difference']

    list_filter = (
        ('week', DateRangeFilter),
        ('member__team__name', AllValuesFieldListFilter),
    )

    search_fields = (
        'member__team__name',
    )

    def get_queryset(self, request):
        qs = super(TimeLogSummaryAdmin, self).get_queryset(request)
        qs = qs.order_by('-week', 'member__team').distinct('member__team', 'week')
        return qs

    @admin.display
    def members(self, instance: TimeLogSummary):
        return format_html(instance.get_members())

    @admin.display
    def projects(self, instance: TimeLogSummary):
        return format_html(instance.get_projects())

    @classmethod
    def team(cls, instance: TimeLogSummary):
        return instance.member.team.name

    @classmethod
    def project_manager_planned(cls, instance: TimeLogSummary):
        return instance.get_time_planned()

    @classmethod
    def team_lead_logged(cls, instance: TimeLogSummary):
        return instance.get_time_logged()

    @classmethod
    def team_work(cls, instance: TimeLogSummary):
        return instance.get_team_work()

    @classmethod
    def difference(cls, instance: TimeLogSummary):
        return instance.get_difference()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProjectState)
class ProjectStateAdmin(admin.ModelAdmin):
    list_display = ['name', 'projects']

    @classmethod
    def projects(cls, instance: ProjectState):
        return instance.project_set.count()


@admin.register(ProjectManager)
class ProjectManagerAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'projects']

    @classmethod
    def projects(cls, instance: ProjectManager):
        return instance.project_set.count()


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [TimePlanInline, ]
    list_display = ['name', 'state', 'manager']
    list_filter = (
        'state__name',
    )
    search_fields = (
        'name',
    )

    @classmethod
    def state(cls, instance: Project):
        return instance.state.name

    @classmethod
    def manager(cls, instance: Project):
        return instance.manager.fullname


@admin.register(Tech)
class TeamTechAdmin(admin.ModelAdmin):
    list_display = ['name', 'teams']

    @classmethod
    def teams(cls, instance: Tech):
        return instance.team_set.count()


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [TeamMembersInline, ]
    list_display = ['name', 'tech', 'members']
    list_filter = (
        'tech__name',
    )
    search_fields = (
        'name',
    )

    @classmethod
    def members(cls, instance: Team):
        return instance.teammember_set.count()


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    inlines = [TimeLogInline, ]
    list_display = ['fullname', 'team_name', 'team_tech', 'time_logged_in_current_week']
    list_filter = (
        'team__name',
    )
    search_fields = (
        'fullname',
    )

    @classmethod
    def team_name(cls, instance: TeamMember):
        return instance.team.name

    @classmethod
    def team_tech(cls, instance: TeamMember):
        return instance.team.tech

    @classmethod
    def time_logged_in_current_week(cls, instance: TeamMember):
        return instance.get_timelog_for_current_week()
